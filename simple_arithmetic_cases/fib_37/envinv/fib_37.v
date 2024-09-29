module top (
    input wire selector,
    input wire clk,
    input wire rst,
    // output reg [10:0] n,
    output reg [10:0] m,
    output reg [10:0] n,
    output reg [10:0] x
    
);

    always@(posedge clk) begin
        $display("m: %b, n: %b, x: %b", m, n, x);
    end 

    
    always @(posedge clk) begin
        if(rst)begin
            m<=0;
            x<=0;
            n<=200;
        end
        else begin
                if ((x>=n)) begin
                    n<=n;
                    x<=x;
                    m<=m;
                end

                else if((x<n))begin
                    x <= x +1;
                    n<=n;
                    if(selector)
                        m<=x;
                    else
                        m<=m;
                end
            end
        end
    
    // assert property ((x<n)||((m<n)&&(m>=0)));
endmodule