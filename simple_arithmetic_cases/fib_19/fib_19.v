module top (
    input wire selector,
    input wire clk,
    input wire rst
    // output reg [10:0] n,
    // output reg [10:0] m,

    
);

    reg [10:0] x;
    reg [10:0] y;
    
    always @(posedge clk) begin
        if(rst)begin
            y <= 100;
            x<=0;
            b<=0;
        end
        else begin
            // if(selector)begin
                if ((x<200)&&(x+1<=100)) begin
                    x<=x+1;
                    y<=y;
                end
                else if((x<200)&&(x+1>100)&&(y<200)) begin
                    x<=x+1;
                    y<=y + 1;
                end
                else begin
                    x<=x;
                    y<=y;                
                end
            // end
            // else if(!selector) begin
            //         x<=x;
            //         y<=y; 
            // end
        end
    end
    assert property (((x<200)||(y==200)));
endmodule