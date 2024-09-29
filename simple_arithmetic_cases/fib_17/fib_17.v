module top (
    input wire selector,
    input wire clk,
    input wire rst,
    output reg [2:0] turn,
    output reg [10:0] k,
    output reg [10:0] i,
    output reg [10:0] j
    
);


    
    always @(posedge clk) begin
        if(rst)begin
            turn <= 0;
            j<=0;
            k<=1;
            i<=1;
        end
        else begin
            if(k<2000)begin
                if ((turn==0)&&(i<60)) begin
                    k<=k;
                    i<=i;
                    j<=0;
                    turn<=1;
                end
                else if ((turn==0)&&(i>=60))begin
                    k<=k;
                    i<=i;
                    j<=0;
                    turn<=3;
                end
                else if ((turn==1)&&(j<i))begin
                    k<=k + i - j;
                    i<=i;
                    j<=j+1;
                    turn<=turn;
                end
                else if ((turn==1)&&(j>=i))begin
                    k<=k;
                    i<=i;
                    j<=j;
                    turn<=2;
                end
                else if ((turn==2))begin
                    k<=k;
                    i<=i + 1;
                    j<=j;
                    turn<=0;
                end
                else begin
                    k<=k;
                    i<=i;
                    j<=j;
                    turn<=turn;                    
                end
            end
            else begin
                    k<=k;
                    i<=i;
                    j<=j;
                    turn<=turn;       

            end
        end
    end
    assert property ((turn!=3)||(k>=60));
endmodule